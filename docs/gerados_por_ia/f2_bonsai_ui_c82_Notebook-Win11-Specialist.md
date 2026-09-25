```html:backend/app/static/farmacia_dispensacao.html
<!DOCTYPE html>
<html lang="pt-BR" class="min-h-screen bg-gray-50">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Farmácia UBS - Consulta e Baixa de Prescrição</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * { font-family: 'Inter', sans-serif; }
        body { background: #f0f1f5; }
        .glass-panel {
            background: rgba(255,255,255,0.95);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.3);
            box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        }
        .glass-panel-dark {
            background: rgba(15,23,42,0.95);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
            box-shadow: 0 1px 3px rgba(0,0,0,0.3);
        }
        .scan-ring {
            animation: pulse-ring 2s infinite;
        }
        @keyframes pulse-ring {
            0% { transform: scale(1); opacity: 0.5; }
            50% { transform: scale(1.05); opacity: 0.8; }
            100% { transform: scale(1); opacity: 0.5; }
        }
        .scan-ring:hover {
            animation: pulse-ring 1s infinite;
        }
        .badge-cian { background: #0ea5e9; color: white; }
        .badge-amber { background: #f59e0b; color: white; }
        .badge-emerald { background: #10b981; color: white; }
        .badge-rose { background: #f43f5e; color: white; }
        .badge-violet { background: #8b5cf6; color: white; }
        .badge-slate { background: #64748b; color: white; }
        .scan-input {
            border: 2px solid #e2e8f0;
            transition: all 0.3s ease;
        }
        .scan-input:focus {
            border-color: #0ea5e9;
            box-shadow: 0 0 0 3px rgba(14,165,233,0.15);
        }
        .scan-input::placeholder { color: #94a3b8; }
        .med-card {
            transition: all 0.2s ease;
        }
        .med-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        .med-card dispensed {
            opacity: 0.6;
            cursor: default;
        }
        .med-card dispensed .med-name { text-decoration: line-through; color: #94a3b8; }
        .med-card dispensed .med-qty { color: #64748b; }
        .med-card dispensed .btn-dispense {
            background: #f0f1f5;
            color: #94a3b8;
            cursor: default;
        }
        .med-card dispensed .btn-dispense:hover {
            background: #e2e8f0;
        }
        .alert-box {
            animation: slide-in 0.3s ease-out;
        }
        @keyframes slide-in {
            from { transform: translateY(-10px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }
        .tab-active {
            background: #0ea5e9;
            color: white;
            border-color: #0ea5e9;
        }
        .tab-inactive {
            background: transparent;
            color: #64748b;
            border-color: transparent;
        }
        .tab-inactive:hover {
            background: #f1f5f9;
            color: #334155;
        }
        .progress-bar {
            transition: width 0.5s ease;
        }
        .suspense-bar {
            background: linear-gradient(90deg, #f43f5e 0%, #f97316 50%, #f59e0b 100%);
        }
        .suspense-bar:has([data-level="high"]) { background: linear-gradient(90deg, #f43f5e 0%, #ef4444 100%); }
        .suspense-bar:has([data-level="medium"]) { background: linear-gradient(90deg, #f59e0b 0%, #f97316 100%); }
        .suspense-bar:has([data-level="low"]) { background: linear-gradient(90deg, #10b981 0%, #059669 100%); }
        .suspense-bar:has([data-level="none"]) { background: linear-gradient(90deg, #3b82f6 0%, #2563eb 100%); }
        .tab-btn {
            position: relative;
            transition: all 0.3s ease;
        }
        .tab-btn::after {
            content: '';
            position: absolute;
            bottom: -1px;
            left: 0;
            right: 0;
            height: 2px;
            background: #0ea5e9;
            transform: scaleX(0);
            transition: transform 0.3s ease;
        }
        .tab-btn:hover::after { transform: scaleX(1); }
        .tab-btn.active::after { transform: scaleX(1); }
        .tab-btn.active {
            background: #0ea5e9;
            color: white;
            border-color: #0ea5e9;
        }
        .tab-btn.active:hover { background: #0284c7; }
        .tab-btn.active:hover::after { background: #0ea5e9; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active):hover::after { background: transparent; }
        .tab-btn:not(.active):hover { background: #f1f5f9; color: #334155; border-color: #e2e8f0; }
        .tab-btn:not(.active):hover::after { transform: scaleX(1); }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active):hover::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active):hover::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active)::after { background: transparent; }
        .tab-btn:not(.active