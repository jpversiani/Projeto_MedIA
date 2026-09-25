```python:backend/app/static/farmacia_dispensacao.html
# Arquivo: backend/app/static/farmacia_dispensacao.html
<!DOCTYPE html>
<html lang="pt-BR" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Farmácia UBS — Consulta & Baixa de Prescrição</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * { font-family: 'Inter', sans-serif; }
        body { background: #0f172a; color: #e2e8f0; }
        .glass { background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.08); }
        .glass-card { background: rgba(15, 23, 42, 0.9); backdrop-filter: blur(8px); border: 1px solid rgba(255,255,255,0.06); }
        .scan-zone {
            border: 2px dashed rgba(59, 130, 246, 0.4);
            transition: all 0.3s ease;
        }
        .scan-zone:hover, .scan-zone.active {
            border-color: #3b82f6;
            background: rgba(59, 130, 246, 0.05);
            box-shadow: 0 0 20px rgba(59, 130, 246, 0.15);
        }
        .scan-zone .scan-hint {
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 0.6; }
            50% { opacity: 1; }
        }
        .btn-primary { background: linear-gradient(135deg, #3b82f6, #2563eb); }
        .btn-primary:hover { background: linear-gradient(135deg, #2563eb, #1d4ed8); }
        .btn-danger { background: linear-gradient(135deg, #ef4444, #dc2626); }
        .btn-danger:hover { background: linear-gradient(135deg, #dc2626, #b91c1c); }
        .btn-success { background: linear-gradient(135deg, #10b981, #059669); }
        .btn-success:hover { background: linear-gradient(135deg, #059669, #047857); }
        .btn-outline { background: transparent; border: 1px solid rgba(255,255,255,0.15); }
        .btn-outline:hover { border-color: rgba(255,255,255,0.3); }
        .badge-sus { background: rgba(59, 130, 246, 0.15); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.3); }
        .badge-aps { background: rgba(16, 185, 129, 0.15); color: #6ee7b7; border: 1px solid rgba(16, 185, 129, 0.3); }
        .badge-soap { background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }
        .badge-ciap2 { background: rgba(148, 163, 184, 0.15); color: #cbd5e1; border: 1px solid rgba(148, 163, 184, 0.3); }
        .badge-cid10 { background: rgba(236, 72, 153, 0.15); color: #f472b6; border: 1px solid rgba(236, 72, 153, 0.3); }
        .badge-cpf { background: rgba(234, 179, 8, 0.15); color: #fbbf24; border: 1px solid rgba(234, 179, 8, 0.3); }
        .badge-cns { background: rgba(236, 72, 153, 0.15); color: #f472b6; border: 1px solid rgba(236, 72, 153, 0.3); }
        .scan-ring {
            width: 120px; height: 120px;
            border-radius: 50%;
            border: 2px solid rgba(59, 130, 246, 0.3);
            position: relative;
        }
        .scan-ring::before {
            content: '';
            position: absolute;
            inset: 15px;
            border-radius: 50%;
            border: 1px solid rgba(59, 130, 246, 0.15);
        }
        .scan-ring::after {
            content: '';
            position: absolute;
            inset: 25px;
            border-radius: 50%;
            border: 1px solid rgba(59, 130, 246, 0.1);
        }
        .scan-ring .inner {
            width: 40px; height: 40px;
            border-radius: 50%;
            background: rgba(59, 130, 246, 0.2);
            border: 2px solid rgba(59, 130, 246, 0.6);
        }
        .scan-ring .inner::before, .scan-ring .inner::after {
            content: '';
            position: absolute;
            width: 100%; height: 100%;
            border-radius: 50%;
            border: 1px solid rgba(59, 130, 246, 0.5);
            animation: spin 2s linear infinite;
        }
        .scan-ring .inner::before { animation-direction: reverse; }
        @keyframes spin { to { transform: rotate(360deg); } }
        .prescription-card {
            transition: all 0.3s ease;
        }
        .prescription-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        }
        .tab-panel { display: none; }
        .tab-panel.active { display: block; animation: fadeIn 0.3s ease; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }
        .tab-panel.active + .tab-panel { display: none; }
        .tab-panel.active ~ .tab-panel { display: block; animation: fadeIn 0.3s ease; }
        .tab-panel.active ~ .tab-panel ~ .tab-panel { display: none; }
        .tab-panel.active ~ .tab-panel ~ .tab-panel ~ .tab-panel { display: block; animation: fadeIn 0.3s ease; }
        .tab-panel.active ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel { display: none; }
        .tab-panel.active ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel { display: block; animation: fadeIn 0.3s ease; }
        .tab-panel.active ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel { display: none; }
        .tab-panel.active ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel { display: block; animation: fadeIn 0.3s ease; }
        .tab-panel.active ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel { display: none; }
        .tab-panel.active ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel { display: block; animation: fadeIn 0.3s ease; }
        .tab-panel.active ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel { display: none; }
        .tab-panel.active ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel { display: block; animation: fadeIn 0.3s ease; }
        .tab-panel.active ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~ .tab-panel ~