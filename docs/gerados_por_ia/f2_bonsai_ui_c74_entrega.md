```html:backend/app/static/farmacia_dispensacao.html
<!DOCTYPE html>
<html lang="pt-BR" class="min-h-screen">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Farmacia Dispensação - UBS MedIA</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&display=swap');

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', sans-serif;
            background: #0f172a;
            color: #e2e8f0;
            overflow-x: hidden;
        }

        .mono {
            font-family: 'JetBrains Mono', monospace;
        }

        /* Scanline effect */
        .scanline {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 9999;
            background: repeating-linear-gradient(
                0deg,
                transparent,
                transparent 2px,
                rgba(0, 0, 0, 0.1) 2px,
                rgba(0, 0, 0, 0.1) 4px
            );
        }

        /* CRT glow */
        .crt-glow {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 9998;
            background: radial-gradient(ellipse at center, transparent 60%, rgba(0, 0, 0, 0.4) 100%);
        }

        /* Scan area */
        .scan-area {
            position: relative;
            width: 100%;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            background: rgba(15, 23, 42, 0.95);
            border: 2px solid #334155;
            border-radius: 12px;
            overflow: hidden;
        }

        .scan-area::before {
            content: '';
            position: absolute;
            inset: 0;
            background: radial-gradient(ellipse at center, rgba(56, 189, 248, 0.05) 0%, transparent 70%);
            pointer-events: none;
        }

        .scan-frame {
            width: 100%;
            height: 100%;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            position: relative;
        }

        .scan-border {
            position: absolute;
            inset: 0;
            border: 2px solid #38bdf8;
            border-radius: 8px;
            pointer-events: none;
            animation: pulse-border 2s infinite;
        }

        @keyframes pulse-border {
            0%, 100% { opacity: 0.6; }
            50% { opacity: 1; }
        }

        .scan-border::before {
            content: '';
            position: absolute;
            inset: 4px;
            border: 1px solid rgba(56, 189, 248, 0.3);
            border-radius: 4px;
        }

        .scan-border::after {
            content: '';
            position: absolute;
            inset: 8px;
            border: 1px solid rgba(56, 189, 248, 0.15);
            border-radius: 4px;
        }

        .scan-content {
            position: relative;
            z-index: 1;
            text-align: center;
        }

        .scan-icon {
            width: 80px;
            height: 80px;
            border: 2px solid #38bdf8;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 16px;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); }
        }

        .scan-icon svg {
            width: 40px;
            height: 40px;
            color: #38bdf8;
        }

        .scan-text {
            font-size: 1.1rem;
            color: #94a3b8;
            margin-bottom: 8px;
        }

        .scan-text strong {
            color: #38bdf8;
        }

        .scan-input {
            width: 100%;
            max-width: 400px;
            padding: 12px 20px;
            background: rgba(15, 23, 42, 0.8);
            border: 2px solid #334155;
            border-radius: 8px;
            color: #e2e8f0;
            font-family: 'JetBrains Mono', monospace;
            font-size: 1.1rem;
            text-align: center;
            outline: none;
            transition: all 0.3s ease;
            letter-spacing: 2px;
        }

        .scan-input::placeholder {
            color: #475569;
        }

        .scan-input:focus {
            border-color: #38bdf8;
            box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.2);
        }

        .scan-input.scanning {
            border-color: #38bdf8;
            background: rgba(56, 189, 248, 0.05);
            animation: scan-pulse 0.5s infinite;
        }

        @keyframes scan-pulse {
            0%, 100% { box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.2); }
            50% { box-shadow: 0 0 0 6px rgba(56, 189, 248, 0.4); }
        }

        .scan-btn {
            width: 100%;
            max-width: 400px;
            padding: 14px 32px;
            background: linear-gradient(135deg, #38bdf8, #2563eb);
            border: none;
            border-radius: 8px;
            color: white;
            font-family: 'Inter', sans-serif;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-top: 12px;
            letter-spacing: 1px;
        }

        .scan-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(56, 189, 248, 0.3);
        }

        .scan-btn:active {
            transform: translateY(0);
        }

        .scan-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }

        /* Main content area */
        .main-content {
            display: none;
            max-width: 1400px;
            margin: 0 auto;
            padding: 24px;
        }

        .main-content.visible {
            display: block;
            animation: fadeIn 0.5s ease;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* Header */
        .app-header {
            background: rgba(15, 23, 42, 0.8);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(51, 65, 85, 0.5);
            border-radius: 16px;
            padding: 24px 32px;
            margin-bottom: 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 24px;
        }

        .header-brand {
            display: flex;
            align-items: center;
            gap: 16px;
        }

        .header-brand-logo {
            width: 48px;
            height: 48px;
            background: linear-gradient(135deg, #38bdf8, #2563eb);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            font-size: 1.2rem;
            color: white;
        }

        .header-brand-text h1 {
            font-size: 1.5rem;
            font-weight: 800;
            color: white;
            letter-spacing: -0.5px;
        }

        .header-brand-text p {
            font-size: 0.8rem;
            color: #94a3b8;
            font-weight: 500;
        }

        .header-actions {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .user-badge {
            display: flex;
            align-items: center;
            gap: 10px;
            background: rgba(51, 65, 85, 0.5);
            border: 1px solid rgba(51, 65, 85, 0.8);
            border-radius: 100px;
            padding: 8px 16px;
        }

        .user-avatar {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            background: linear-gradient(135deg, #38bdf8, #2563eb);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 0.85rem;
            color: white;
        }

        .user-info {
            display: flex;
            flex-direction: column;
        }

        .user-info span {
            font-size: 0.8rem;
            font-weight: 600;
            color: white;
        }

        .user-info small {
            font-size: 0.7rem;
            color: #94a3b8;
        }

        .header-actions button {
            background: rgba(51, 65, 85, 0.5);
            border: 1px solid rgba(51, 65, 85, 0.8);
            color: white;
            padding: 8px 16px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.85rem;
            font-weight: 500;
            transition: all 0.3s ease;
        }

        .header-actions button:hover {
            background: rgba(51, 65, 85, 0.8);
        }

        /* Sidebar */
        .sidebar {
            position: fixed;
            left: 0;
            top: 0;
            bottom: 0;
            width: 280px;
            background: rgba(15, 23, 42, 0.95);
            backdrop-filter: blur(20px);
            border-right: 1px solid rgba(51, 65, 85, 0.5);
            padding: 24px 16px;
            z-index: 100;
            display: flex;
            flex-direction: column;
        }

        .sidebar-nav {
            flex: 1;
            overflow-y: auto;
        }

        .sidebar-nav-section {
            margin-bottom: 24px;
        }

        .sidebar-nav-section-title {
            font-size: 0.7rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            color: #475569;
            padding: 0 8px;
            margin-bottom: 8px;
        }

        .sidebar-nav-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 10px 12px;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s ease;
            font-size: 0.9rem;
            color: #94a3b8;
            margin-bottom: 4px;
        }

        .sidebar-nav-item:hover {
            background: rgba(51, 65, 85, 0.3);
            color: white;
        }

        .sidebar-nav-item.active {
            background: rgba(56, 189, 248, 0.1);
            color: #38bdf8;
        }

        .sidebar-nav-item svg {
            width: 20px;
            height: 20px;
            flex-shrink: 0;
        }

        .sidebar-bottom {
            padding: 16px;
            border-top: 1px solid rgba(51, 65, 85, 0.5);
            margin-top: auto;
        }

        .sidebar-status {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.8rem;
            color: #94a3b8;