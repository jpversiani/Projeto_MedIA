```html:backend/app/static/farmacia_dispensacao.html
<!DOCTYPE html>
<html lang="pt-BR" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Farmácia Dispensação - UBS</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
    <style>
        * {
            font-family: 'Inter', sans-serif;
        }

        body {
            background-color: #f0f2f5;
            color: #1a1a2e;
        }

        .glass-panel {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.3);
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        }

        .glass-panel-dark {
            background: rgba(26, 26, 46, 0.95);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
        }

        .scan-zone {
            transition: all 0.3s ease;
            border: 2px dashed #e5e7eb;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-direction: column;
            gap: 12px;
        }

        .scan-zone:hover, .scan-zone:focus {
            border-color: #3b82f6;
            background: rgba(59, 130, 246, 0.05);
        }

        .scan-zone.scanning {
            border-color: #10b981;
            background: rgba(16, 185, 129, 0.1);
            animation: pulse-scan 1s infinite;
        }

        @keyframes pulse-scan {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }

        .scan-ring {
            width: 60px;
            height: 60px;
            border: 2px solid #3b82f6;
            border-radius: 50%;
            position: relative;
            animation: rotate 2s linear infinite;
        }

        .scan-ring::before {
            content: '';
            position: absolute;
            width: 100%;
            height: 100%;
            border-radius: 50%;
            border: 2px solid #3b82f6;
            animation: rotate 2s linear infinite;
        }

        @keyframes rotate {
            to { transform: rotate(360deg); }
        }

        .patient-card {
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }

        .patient-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
        }

        .medication-pill {
            transition: all 0.3s ease;
        }

        .medication-pill:hover {
            transform: scale(1.02);
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
        }

        .status-badge {
            transition: all 0.3s ease;
        }

        .status-badge.active {
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.4); }
            70% { box-shadow: 0 0 0 10px rgba(16, 185, 129, 0); }
        }

        .btn-primary {
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
            transition: all 0.3s ease;
        }

        .btn-primary:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
        }

        .btn-primary:active {
            transform: translateY(0);
        }

        .btn-success {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            transition: all 0.3s ease;
        }

        .btn-success:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4);
        }

        .btn-danger {
            background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
            transition: all 0.3s ease;
        }

        .btn-danger:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(239, 68, 68, 0.4);
        }

        .btn-outline {
            background: transparent;
            border: 2px solid #e5e7eb;
            transition: all 0.3s ease;
        }

        .btn-outline:hover {
            border-color: #3b82f6;
            background: rgba(59, 130, 246, 0.05);
        }

        .tab-panel {
            animation: fadeIn 0.3s ease;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .tab-panel.active {
            animation: none;
        }

        .tab-panel:not(.active) {
            display: none;
        }

        .tab-panel:not(.active) > * {
            display: none;
        }

        .tab-panel.active > * {
            display: block;
        }

        .tab-panel.active > .tab-panel {
            display: block;
        }

        .tab-panel.active > .tab-panel > * {
            display: block;
        }

        .tab-panel.active > .tab-panel > .tab-panel {
            display: block;
        }

        .tab-panel.active > .tab-panel > .tab-panel > * {
            display: block;
        }

        .tab-panel.active > .tab-panel > .tab-panel > .tab-panel {
            display: block;
        }

        .tab-panel.active > .tab-panel > .tab-panel > .tab-panel > * {
            display: block;
        }

        .tab-panel.active > .tab-panel > .tab-panel > .tab-panel > .tab-panel {
            display: block;
        }

        .tab-panel.active > .tab-panel > .tab-panel > .tab-panel > .tab-panel > * {
            display: block;
        }

        .tab-panel.active > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel {
            display: block;
        }

        .tab-panel.active > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > * {
            display: block;
        }

        .tab-panel.active > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel {
            display: block;
        }

        .tab-panel.active > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > * {
            display: block;
        }

        .tab-panel.active > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel {
            display: block;
        }

        .tab-panel.active > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > * {
            display: block;
        }

        .tab-panel.active > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > * {
            display: block;
        }

        .tab-panel.active > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel {
            display: block;
        }

        .tab-panel.active > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > * {
            display: block;
        }

        .tab-panel.active > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > * {
            display: block;
        }

        .tab-panel.active > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > * {
            display: block;
        }

        .tab-panel.active > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > * {
            display: block;
        }

        .tab-panel.active > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > * {
            display: block;
        }

        .tab-panel.active > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > * {
            display: block;
        }

        .tab-panel.active > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > * {
            display: block;
        }

        .tab-panel.active > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > * {
            display: block;
        }

        .tab-panel.active > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > * {
            display: block;
        }

        .tab-panel.active > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > * {
            display: block;
        }

        .tab-panel.active > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > * {
            display: block;
        }

        .tab-panel.active > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > * {
            display: block;
        }

        .tab-panel.active > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > * {
            display: block;
        }

        .tab-panel.active > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > * {
            display: block;
        }

        .tab-panel.active > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > * {
            display: block;
        }

        .tab-panel.active > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > * {
            display: block;
        }

        .tab-panel.active > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > * {
            display: block;
        }

        .tab-panel.active > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > * {
            display: block;
        }

        .tab-panel.active > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel > * {
            display: block;
        }

        .tab-panel.active > .tab-panel > .tab-panel > .tab-panel > .tab-panel > .tab-panel