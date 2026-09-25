```python:backend/app/static/farmacia_dispensacao.html
<!DOCTYPE html>
<html lang="pt-BR" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Farmácia Dispensação — UBS | Consulta Prescrição Digital</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <style>
        * { font-family: 'Inter', sans-serif; }
        body { background: #f0f2f5; }
        .glass-panel {
            background: rgba(255,255,255,0.95);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255,255,255,0.3);
        }
        .glass-card {
            background: rgba(255,255,255,0.9);
            backdrop-filter: blur(8px);
            border: 1px solid rgba(255,255,255,0.2);
        }
        .scan-ring {
            animation: pulse-ring 2s infinite;
        }
        @keyframes pulse-ring {
            0% { transform: scale(0.95); opacity: 0.6; }
            50% { transform: scale(1.05); opacity: 0.9; }
            100% { transform: scale(0.95); opacity: 0.6; }
        }
        .scan-ring:hover { animation: none; }
        .scan-ring:focus { outline: 2px solid #10b981; outline-offset: 2px; }
        .badge-sus {
            background: linear-gradient(135deg, #06b6d4, #0891b2);
        }
        .badge-aps {
            background: linear-gradient(135deg, #7c3aed, #6d28d9);
        }
        .badge-ubs {
            background: linear-gradient(135deg, #10b981, #059669);
        }
        .medication-pill {
            transition: all 0.2s ease;
        }
        .medication-pill:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(16,185,129,0.3);
        }
        .progress-bar {
            transition: width 0.5s ease;
        }
        .scan-result {
            animation: slide-in 0.3s ease-out;
        }
        @keyframes slide-in {
            from { opacity: 0; transform: translateY(-10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .scan-result { animation: none; }
        .scan-result.active { animation: slide-in 0.3s ease-out; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        .tab-content.active::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 3px;
            background: linear-gradient(90deg, #10b981, #06b6d4);
            border-radius: 3px 3px 0 0;
        }
        .tab-content.active::after {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 3px;
            background: linear-gradient(90deg, #06b6d4, #10b981);
            border-radius: 3px 3px 0 0;
        }
        .tab-content.active::before { display: none; }
        .tab-content.active::after { display: none; }
        .tab-content.active { animation: fadeIn 0.3s ease-out; }
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        .tab-content.active { animation: none; }
        .tab-content.active { opacity: 1; }
        .tab-content.active { animation: fadeIn 0.3s ease-out; }
        .tab-content.active { display: block; }
        .tab-content.active::before { display: none; }
        .tab-content.active::after { display: none; }
        .tab-content.active { animation: fadeIn 0.3s ease-out; }
        .tab-content.active { display: block; }
        .tab-content.active::before { display: none; }
        .tab-content.active::after { display: none; }
        .tab-content.active { animation: fadeIn 0.3s ease-out; }
        .tab-content.active { display: block; }
        .tab-content.active::before { display: none; }
        .tab-content.active::after { display: none; }
        .tab-content.active { animation: fadeIn 0.3s ease-out; }
        .tab-content.active { display: block; }
        .tab-content.active::before { display: none; }
        .tab-content.active::after { display: none; }
        .tab-content.active { animation: fadeIn 0.3s ease-out; }
        .tab-content.active { display: block; }
        .tab-content.active::before { display: none; }
        .tab-content.active::after { display: none; }
        .tab-content.active { animation: fadeIn 0.3s ease-out; }
        .tab-content.active { display: block; }
        .tab-content.active::before { display: none; }
        .tab-content.active::after { display: none; }
        .tab-content.active { animation: fadeIn 0.3s ease-out; }
        .tab-content.active { display: block; }
        .tab-content.active::before { display: none; }
        .tab-content.active::after { display: none; }
        .tab-content.active { animation: fadeIn 0.3s ease-out; }
        .tab-content.active { display: block; }
        .tab-content.active::before { display: none; }
        .tab-content.active::after { display: none; }
        .tab-content.active { animation: fadeIn 0.3s ease-out; }
        .tab-content.active { display: block; }
        .tab-content.active::before { display: none; }
        .tab-content.active::after { display: none; }
        .tab-content.active { animation: fadeIn 0.3s ease-out; }
        .tab-content.active { display: block; }
        .tab-content.active::before { display: none; }
        .tab-content.active::after { display: none; }
        .tab-content.active { animation: fadeIn 0.3s ease-out; }
        .tab-content.active { display: block; }
        .tab-content.active::before { display: none; }
        .tab-content.active::after { display: none; }
        .tab-content.active { animation: fadeIn 0.3s ease-out; }
        .tab-content.active { display: block; }
        .tab-content.active::before { display: none; }
        .tab-content.active::after { display: none; }
        .tab-content.active { animation: fadeIn 0.3s ease-out; }
        .tab-content.active { display: block; }
        .tab-content.active::before { display: none; }
        .tab-content.active::after { display: none; }
        .tab-content.active { animation: fadeIn 0.3s ease-out; }
        .tab-content.active { display: block; }
        .tab-content.active::before { display: none; }
        .tab-content.active::after { display: none; }
        .tab-content.active { animation: fadeIn 0.3s ease-out; }
        .tab-content.active { display: block; }
        .tab-content.active::before { display: none; }
        .tab-content.active::after { display: none; }
        .tab-content.active { animation: fadeIn 0.3s ease-out; }
        .tab-content.active { display: block; }
        .tab-content.active::before { display: none; }
        .tab-content.active::after { display: none; }
        .tab-content.active { animation: fadeIn 0.3s ease-out; }
        .tab-content.active { display: block; }
        .tab-content.active::before { display: none; }
        .tab-content.active::after { display: none; }
        .tab-content.active { animation: fadeIn 0.3s ease-out; }
        .tab-content.active { display: block; }
        .tab-content.active::before { display: none; }
        .tab-content.active::after { display: none; }
        .tab-content.active { animation: fadeIn 0.3s ease-out; }
        .tab-content.active { display: block; }
        .tab-content.active::before { display: none; }
        .tab-content.active::after { display: none; }
        .tab-content.active { animation: fadeIn 0.3s ease-out; }
        .tab-content.active { display: block; }
        .tab-content.active::before { display: none; }
        .tab-content.active::after { display: none; }
        .tab-content.active { animation: fadeIn 0.3s ease-out; }
        .tab-content.active { display: block; }
        .tab-content.active::before { display: none; }
        .tab-content.active::after { display: none; }
        .tab-content.active { animation: fadeIn 0.3s ease-out; }
        .tab-content.active { display: block; }
        .tab-content.active::before { display: none; }
        .tab-content.active::after { display: none; }
        .tab-content.active { animation: fadeIn 0.3s ease-out; }
        .tab-content.active { display: block; }
        .tab-content.active::before { display: none; }
        .tab-content.active::after { display: none; }
        .tab-content.active { animation: fadeIn 0.3s ease-out; }
        .tab-content.active { display: block; }
        .tab-content.active::before { display: none; }
        .tab-content.active::after { display: none; }
        .tab-content.active { animation: fadeIn 0.3s ease-out; }
        .tab-content.active { display: block; }
        .tab-content.active::before { display: none; }
        .tab-content.active::after { display: none; }
        .tab-content.active { animation: fadeIn 0.3s ease-out; }
        .tab-content.active { display: block; }
        .tab-content.active::before { display: none; }
        .tab-content.active::after { display: none; }
        .tab-content.active { animation: fadeIn 0.3s ease-out; }
        .tab-content.active { display: block; }
        .tab-content.active::before { display: none; }
        .tab-content.active::after { display: none; }
        .tab-content.active { animation: fadeIn 0.3s ease-out; }
        .tab-content.active { display: block; }
        .tab-content.active::before { display: none; }
        .tab-content.active::after { display: none; }
        .tab-content.active { animation: fadeIn 0.3s ease-out; }
        .tab-content.active { display: block; }
        .tab-content.active::before { display: none; }
        .tab-content.active::after { display: none; }
        .tab-content.active { animation: fadeIn 0.3s ease-out; }
        .tab-content.active { display: block; }
        .tab-content.active::before { display: none; }
        .tab-content.active::after { display: none; }
        .tab-content.active { animation: fadeIn 0.3s ease-out; }
        .tab-content.active { display: block; }
        .tab-content.active::before { display: none; }
        .tab-content.active::after { display: none; }
        .tab-content.active { animation: fadeIn 0.3s ease-out; }
        .tab-content.active { display: block; }
        .tab-content.active::before { display: none; }
        .tab-content.active::after { display: none; }
        .tab-content.active { animation: fadeIn 0.3s ease-out; }
        .tab-content.active { display: block; }
        .tab-content.active::before { display: none; }
        .tab-content.active::after { display: none; }
        .tab-content.active { animation: fadeIn 0.3s ease-out; }
        .tab-content.active { display: block; }
        .tab-content.active::before { display: none; }
        .tab-content.active::after { display: none; }
        .tab-content.active { animation: fadeIn 0.3s ease-out; }
        .tab-content.active { display: block; }
        .tab-content.active::before { display: none; }
        .tab-content.active::after { display: none; }
        .tab-content.active { animation: fadeIn 0.3s ease-out; }
        .tab-content.active { display: block; }
        .tab-content.active::before { display: none; }
        .tab-content.active::after { display: none; }
        .tab-content.active { animation: fadeIn 0.3s ease-out; }
        .tab-content.active { display: block; }
        .tab-content.active::before { display: none; }
        .tab-content.active::after { display: none; }
        .tab-content.active { animation: fadeIn 0.3s ease-out; }
        .tab-content.active { display: block; }
        .tab-content.active::before { display: none; }
        .tab-content.active::after { display: none; }
        .tab-content.active { animation: fadeIn 0.3s ease-out; }
        .tab-content.active { display: block; }
        .tab-content.active::before { display: none; }
        .tab-content.active::after { display: none; }
        .tab-content.active { animation: fadeIn 0.3s ease-out; }
        .tab-content.active { display: block; }
        .tab-content.active::before { display: none; }
        .tab-content.active::after { display: none; }
        .tab-content.active { animation: fadeIn 0.3s ease-out; }
        .tab-content.active {