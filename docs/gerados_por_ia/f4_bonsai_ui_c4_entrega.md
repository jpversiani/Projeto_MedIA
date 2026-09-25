```html:backend/app/static/painel_convenios.html
<!DOCTYPE html>
<html lang="pt-BR" class="min-h-screen bg-slate-50">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Painel Convenios e Recibos de Reembolso — MedIA</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * { font-family: 'Inter', sans-serif; }
        body { background: #f0f1f5; }
        .glass-panel {
            background: rgba(255,255,255,0.92);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255,255,255,0.6);
            border-radius: 16px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.06);
        }
        .glass-card {
            background: rgba(255,255,255,0.95);
            backdrop-filter: blur(8px);
            border: 1px solid rgba(255,255,255,0.5);
            border-radius: 12px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.04);
        }
        .stat-card {
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
            border-radius: 14px;
            padding: 24px;
            color: white;
            box-shadow: 0 4px 20px rgba(99,102,241,0.25);
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .stat-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 30px rgba(99,102,241,0.35);
        }
        .stat-card.green {
            background: linear-gradient(135deg, #059669 0%, #10b981 100%);
        }
        .stat-card.red {
            background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%);
        }
        .stat-card.amber {
            background: linear-gradient(135deg, #d97706 0%, #f59e0b 100%);
        }
        .stat-card.blue {
            background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
        }
        .stat-card.purple {
            background: linear-gradient(135deg, #7c3aed 0%, #a855f7 100%);
        }
        .stat-card.teal {
            background: linear-gradient(135deg, #0891b2 0%, #14b8a6 100%);
        }
        .stat-card.cyan {
            background: linear-gradient(135deg, #06b6d4 0%, #22d3ee 100%);
        }
        .stat-card.rose {
            background: linear-gradient(135deg, #db2777 0%, #f43f5e 100%);
        }
        .stat-card.emerald {
            background: linear-gradient(135deg, #065f46 0%, #059669 100%);
        }
        .stat-card.slate {
            background: linear-gradient(135deg, #374151 0%, #64748b 100%);
        }
        .stat-card.amber {
            background: linear-gradient(135deg, #b45309 0%, #f59e0b 100%);
        }
        .stat-card.rose {
            background: linear-gradient(135deg, #991b1b 0%, #ef4444 100%);
        }
        .stat-card.pink {
            background: linear-gradient(135deg, #7f1d1d 0%, #ec4899 100%);
        }
        .stat-card.violet {
            background: linear-gradient(135deg, #581c87 0%, #c084fc 100%);
        }
        .stat-card.rose {
            background: linear-gradient(135deg, #991b1b 0%, #ef4444 100%);
        }
        .stat-card.rose {
            background: linear-gradient(135deg, #991b1b 0%, #ef4444 100%);
        }
        .stat-card.rose {
            background: linear-gradient(135deg, #991b1b 0%, #ef4444 100%);
        }
        .stat-card.rose {
            background: linear-gradient(135deg, #991b1b 0%, #ef4444 100%);
        }
        .stat-card.rose {
            background: linear-gradient(135deg, #991b1b 0%, #ef4444 100%);
        }
        .stat-card.rose {
            background: linear-gradient(135deg, #991b1b 0%, #ef4444 100%);
        }
        .stat-card.rose {
            background: linear-gradient(135deg, #991b1b 0%, #ef4444 100%);
        }
        .stat-card.rose {
            background: linear-gradient(135deg, #991b1b 0%, #ef4444 100%);
        }
        .stat-card.rose {
            background: linear-gradient(135deg, #991b1b 0%, #ef4444 100%);
        }
        .stat-card.rose {
            background: linear-gradient(135deg, #991b1b 0%, #ef4444 100%);
        }
        .stat-card.rose {
            background: linear-gradient(135deg, #991b1b 0%, #ef4444 100%);
        }
        .stat-card.rose {
            background: linear-gradient(135deg, #991b1b 0%, #ef4444 100%);
        }
        .stat-card.rose {
            background: linear-gradient(135deg, #991b1b 0%, #ef4444 100%);
        }
        .stat-card.rose {
            background: linear-gradient(135deg, #991b1b 0%, #ef4444 100%);
        }
        .stat-card.rose {
            background: linear-gradient(135deg, #991b1b 0%, #ef4444 100%);
        }
        .stat-card.rose {
            background: linear-gradient(135deg, #991b1b 0%, #ef4444 100%);
        }
        .stat-card.rose {
            background: linear-gradient(135deg, #991b1b 0%, #ef4444 100%);
        }
        .stat-card.rose {
            background: linear-gradient(135deg, #991b1b 0%, #ef4444 100%);
        }
        .stat-card.rose {
            background: linear-gradient(135deg, #991b1b 0%, #ef4444 100%);
        }
        .stat-card.rose {
            background: linear-gradient(135deg, #991b1b 0%, #ef4444 100%);
        }
        .stat-card.rose {
            background: linear-gradient(135deg, #991b1b 0%, #ef4444 100%);
        }
        .stat-card.rose {
            background: linear-gradient(135deg, #991b1b 0%, #ef4444 100%);
        }
        .stat-card.rose {
            background: linear-gradient(135deg, #991b1b 0%, #ef4444 100%);
        }
        .stat-card.rose {
            background: linear-gradient(135deg, #991b1b 0%, #ef4444 100%);
        }
        .stat-card.rose {
            background: linear-gradient(135deg, #991b1b 0%, #ef4444 100%);
        }
        .stat-card.rose {
            background: linear-gradient(135deg, #991b1b 0%, #ef4444 100%);
        }
        .stat-card.rose {
            background: linear-gradient(135deg, #991b1b 0%, #ef4444 100%);
        }
        .stat-card.rose {
            background: linear-gradient(135deg, #991b1b 0%, #ef4444 100%);
        }
        .stat-card.rose {
            background: linear-gradient(135deg, #991b1b 0%, #ef4444 100%);
        }
        .stat-card.rose {
            background: linear-gradient(135deg, #991b1b 0%, #ef4444 100%);
        }
        .stat-card.rose {
            background: linear-gradient(135deg, #991b1b 0%, #ef4444 100%);
        }
        .stat-card.rose {
            background: linear-gradient(135deg, #991b1b 0%, #ef4444 100%);
        }
        .stat-card.rose {
            background: linear-gradient(135deg, #991b1b 0%, #ef4444 100%);
        }
        .stat-card.rose {
            background: linear-gradient(135deg, #991b1b 0%, #ef4444 100%);
        }
        .stat-card.rose {
            background: linear-gradient(135deg, #991b1b 0%, #ef4444 100%);
        }
        .stat-card.rose {
            background: linear-gradient(135deg, #991b1b 0%, #ef4444 100%);
        }
        .stat-card.rose {
            background: linear-gradient(135deg, #991b1b 0%, #ef4444 100%);
        }
        .stat-card.rose {
            background: linear-gradient(135deg, #991b1b 0%, #ef4444 100%);
        }
        .stat-card.rose {
            background: linear-gradient(135deg, #991b1b 0%, #ef4444 100%);
        }
        .stat-card.rose {
            background: linear-gradient(135deg, #991b1b 0%, #ef4444 100%);
        }
        .stat-card.rose {
            background: linear-gradient(135deg, #991b1b 0%, #ef4444 100%);
        }
        .stat-card.rose {
            background: linear-gradient(135deg, #991b1b 0%, #ef4444 100%);
        }
        .stat-card.rose {
            background: linear-gradient(135deg, #991b1b 0%, #ef4444 100%);
        }
        .stat-card.rose {
            background: linear-gradient(135deg, #991b1b 0%, #ef4444 100%);
        }
        .stat-card.rose {
            background: linear-gradient(135deg, #991b1b 0%, #ef4444 100%);
        }
        .stat-card.rose {
            background: linear-gradient(135deg, #991b1b 0%, #ef4444 100%);
        }
        .stat-card.rose {
            background: linear-gradient(135deg, #991b1b 0%, #ef4444 100%);
        }
        .stat-card.rose {
            background: linear-gradient(135deg, #991b1b 0%, #ef4444 100%);
        }
        .stat-card.rose {
            background: linear-gradient(135deg, #991b1b 0%, #ef4444 100%);
        }
        .stat-card.rose {
            background: linear-gradient(135deg, #991b1b 0%, #ef4444 100%);
        }
        .stat-card.rose {
            background: linear-gradient(135deg, #991b1b 0%, #ef4444 100%);
        }
        .stat-card.rose {
            background: linear-gradient(