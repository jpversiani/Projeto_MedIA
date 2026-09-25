```html:backend/app/static/farmacia_dispensacao.html
# Arquivo: backend/app/static/farmacia_dispensacao.html

<!DOCTYPE html>
<html lang="pt-BR" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Farmácia Dispensação — UBS MedIA</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <style>
        * { font-family: 'Inter', sans-serif; }
        body { background: #0f172a; color: #e2e8f0; }
        .glass {
            background: rgba(30, 41, 59, 0.7);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(148, 163, 184, 0.08);
        }
        .glass-card {
            background: rgba(15, 23, 42, 0.85);
            backdrop-filter: blur(8px);
            border: 1px solid rgba(148, 163, 184, 0.06);
        }
        .scan-ring {
            animation: scanPulse 2s ease-in-out infinite;
        }
        @keyframes scanPulse {
            0%, 100% { transform: scale(1); opacity: 0.4; }
            50% { transform: scale(1.05); opacity: 0.8; }
        }
        .barcode-scan {
            transition: all 0.3s ease;
        }
        .barcode-scan.active {
            border-color: #34d399;
            box-shadow: 0 0 20px rgba(52, 211, 153, 0.3);
        }
        .badge-cns { background: rgba(59, 130, 246, 0.15); border-color: rgba(59, 130, 246, 0.3); }
        .badge-cpf { background: rgba(244, 114, 182, 0.15); border-color: rgba(244, 114, 182, 0.3); }
        .badge-prescription { background: rgba(245, 158, 11, 0.15); border-color: rgba(245, 158, 11, 0.3); }
        .badge-medication { background: rgba(52, 211, 153, 0.15); border-color: rgba(52, 211, 153, 0.3); }
        .badge-error { background: rgba(239, 68, 68, 0.15); border-color: rgba(239, 68, 68, 0.3); }
        .badge-success { background: rgba(52, 211, 153, 0.15); border-color: rgba(52, 211, 153, 0.3); }
        .badge-warning { background: rgba(245, 158, 11, 0.15); border-color: rgba(245, 158, 11, 0.3); }
        .btn-primary {
            background: linear-gradient(135deg, #3b82f6, #2563eb);
            transition: all 0.2s ease;
        }
        .btn-primary:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 15px rgba(37, 99, 235, 0.4);
        }
        .btn-primary:active { transform: translateY(0); }
        .btn-danger {
            background: linear-gradient(135deg, #ef4444, #dc2626);
            transition: all 0.2s ease;
        }
        .btn-danger:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 15px rgba(239, 68, 68, 0.4);
        }
        .btn-success {
            background: linear-gradient(135deg, #10b981, #059669);
            transition: all 0.2s ease;
        }
        .btn-success:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4);
        }
        .btn-secondary {
            background: rgba(148, 163, 184, 0.1);
            border: 1px solid rgba(148, 163, 184, 0.2);
            transition: all 0.2s ease;
        }
        .btn-secondary:hover {
            background: rgba(148, 163, 184, 0.2);
        }
        .input-glow {
            border: 1px solid rgba(148, 163, 184, 0.2);
            transition: all 0.2s ease;
        }
        .input-glow:focus {
            border-color: #3b82f6;
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
            outline: none;
        }
        .tab-panel {
            animation: fadeSlideIn 0.3s ease;
        }
        @keyframes fadeSlideIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .progress-bar {
            transition: width 0.5s ease;
        }
        .suspense-bar {
            background: linear-gradient(90deg, #3b82f6, #2563eb, #3b82f6);
            background-size: 200% 100%;
            animation: shimmer 1.5s infinite;
        }
        @keyframes shimmer {
            0% { background-position: 200% 0; }
            100% { background-position: -200% 0; }
        }
        .tab-btn.active {
            background: rgba(59, 130, 246, 0.2);
            border-color: rgba(59, 130, 246, 0.4);
            color: #60a5fa;
        }
        .tab-btn.active::after {
            content: '';
            position: absolute;
            bottom: -1px;
            left: 50%;
            transform: translateX(-50%);
            width: 20px;
            height: 3px;
            background: #3b82f6;
            border-radius: 2px;
        }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active)::after { display: none; }
        .tab-btn.active::after { display: block; }
        .tab-btn:not(.active