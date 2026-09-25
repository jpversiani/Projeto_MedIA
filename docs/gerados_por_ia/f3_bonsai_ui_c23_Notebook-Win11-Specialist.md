```html:backend/app/static/painel_triage.html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Painel de Triagem e Monitor de Fila - C23 - SUS/APS</title>
    <style>
        /* ============================================
           PALETA MANCHESTER (C23)
           ============================================ */
        :root {
            --manchester-red: #D90000;
            --manchester-red-dark: #B00000;
            --manchester-red-light: #FF4444;
            --manchester-white: #FFFFFF;
            --manchester-blue: #003366;
            --manchester-blue-light: #4466CC;
            --manchester-black: #1A1A2E;
            --manchester-gray: #2D2D44;
            --manchester-gray-light: #4A4A6A;
            --manchester-gray-dark: #6A6A8A;
            --manchester-green: #008000;
            --manchester-green-light: #4CAF50;
            --manchester-yellow: #FFC107;
            --manchester-orange: #FF9800;
            --shadow-sm: 0 2px 8px rgba(0,0,0,0.1);
            --shadow-md: 0 4px 16px rgba(0,0,0,0.15);
            --shadow-lg: 0 8px 32px rgba(0,0,0,0.2);
            --radius-sm: 8px;
            --radius-md: 12px;
            --radius-lg: 16px;
            --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: linear-gradient(135deg, var(--manchester-gray) 0%, var(--manchester-gray-dark) 100%);
            color: var(--manchester-white);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }

        /* ============================================
           HEADER / BARRA SUPERIOR
           ============================================ */
        .header {
            background: linear-gradient(135deg, var(--manchester-red) 0%, var(--manchester-red-dark) 100%);
            padding: 16px 32px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            box-shadow: var(--shadow-md);
            position: sticky;
            top: 0;
            z-index: 1000;
        }

        .header-brand {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .header-brand-icon {
            width: 48px;
            height: 48px;
            background: var(--manchester-white);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            font-weight: 900;
            color: var(--manchester-red);
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }

        .header-brand-text h1 {
            font-size: 22px;
            font-weight: 800;
            letter-spacing: 0.5px;
        }

        .header-brand-text p {
            font-size: 11px;
            opacity: 0.8;
            letter-spacing: 1px;
            text-transform: uppercase;
        }

        .header-right {
            display: flex;
            align-items: center;
            gap: 20px;
        }

        .header-status {
            display: flex;
            align-items: center;
            gap: 8px;
            background: rgba(255,255,255,0.1);
            padding: 8px 16px;
            border-radius: 50px;
            font-size: 13px;
            font-weight: 600;
        }

        .status-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: var(--manchester-green);
            animation: pulse 2s infinite;
        }

        .status-dot.warning {
            background: var(--manchester-yellow);
            animation: pulse 1s infinite;
        }

        .status-dot.critical {
            background: var(--manchester-red);
            animation: pulse 0.5s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.5; transform: scale(1.5); }
        }

        .header-right .btn-call {
            background: var(--manchester-blue);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 50px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: var(--transition);
            box-shadow: 0 4px 12px rgba(0,51,102,0.4);
        }

        .btn-call:hover {
            background: var(--manchester-blue-light);
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0,51,102,0.5);
        }

        .header-right .btn-call:active {
            transform: translateY(0);
        }

        .header-right .btn-call.calling {
            background: var(--manchester-red);
            animation: pulse 1s infinite;
        }

        .header-right .btn-call.calling .btn-call-icon {
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }

        .header-right .btn-call .btn-call-icon {
            font-size: 18px;
        }

        .header-right .btn-call .btn-call-text {
            font-weight: 700;
        }

        .header-right .btn-call .btn-call-text span {
            font-size: 11px;
            font-weight: 400;
            opacity: 0.8;
        }

        .header-right .btn-call .btn-call-text .call-number {
            color: var(--manchester-red);
            font-weight: 700;
        }

        .header-right .btn-call .btn-call-text .call-number .call-number {
            color: var(--manchester-red);
            font-weight: 700;
        }

        .header-right .btn-call .btn-call-text .call-number .call-number {
            color: var(--manchester-red);
            font-weight: 700;
        }

        .header-right .btn-call .btn-call-text .call-number .call-number {
            color: var(--manchester-red);
            font-weight: 700;
        }

        .header-right .btn-call .btn-call-text .call-number .call-number {
            color: var(--manchester-red);
            font-weight: 700;
        }

        .header-right .btn-call .btn-call-text .call-number .call-number {
            color: var(--manchester-red);
            font-weight: 700;
        }

        .header-right .btn-call .btn-call-text .call-number .call-number {
            color: var(--manchester-red);
            font-weight: 700;
        }

        .header-right .btn-call .btn-call-text .call-number .call-number {
            color: var(--manchester-red);
            font-weight: 700;
        }

        .header-right .btn-call .btn-call-text .call-number .call-number {
            color: var(--manchester-red);
            font-weight: 700;
        }

        .header-right .btn-call .btn-call-text .call-number .call-number {
            color: var(--manchester-red);
            font-weight: 700;
        }

        .header-right .btn-call .btn-call-text .call-number .call-number {
            color: var(--manchester-red);
            font-weight: 700;
        }

        .header-right .btn-call .btn-call-text .call-number .call-number {
            color: var(--manchester-red);
            font-weight: 700;
        }

        .header-right .btn-call .btn-call-text .call-number .call-number {
            color: var(--manchester-red);
            font-weight: 700;
        }

        .header-right .btn-call .btn-call-text .call-number .call-number {
            color: var(--manchester-red);
            font-weight: 700;
        }

        .header-right .btn-call .btn-call-text .call-number .call-number {
            color: var(--manchester-red);
            font-weight: 700;
        }

        .header-right .btn-call .btn-call-text .call-number .call-number {
            color: var(--manchester-red);
            font-weight: 700;
        }

        .header-right .btn-call .btn-call-text .call-number .call-number {
            color: var(--manchester-red);
            font-weight: 700;
        }

        .header-right .btn-call .btn-call-text .call-number .call-number {
            color: var(--manchester-red);
            font-weight: 700;
        }

        .header-right .btn-call .btn-call-text .call-number .call-number {
            color: var(--manchester-red);
            font-weight: 700;
        }

        .header-right .btn-call .btn-call-text .call-number .call-number {
            color: var(--manchester-red);
            font-weight: 700;
        }

        .header-right .btn-call .btn-call-text .call-number .call-number {
            color: var(--manchester-red);
            font-weight: 700;
        }

        .header-right .btn-call .btn-call-text .call-number .call-number {
            color: var(--manchester-red);
            font-weight: 700;
        }

        .header-right .btn-call .btn-call-text .call-number .call-number {
            color: var(--manchester-red);
            font-weight: 700;
        }

        .header-right .btn-call .btn-call-text .call-number .call-number {
            color: var(--manchester-red);
            font-weight: 700;
        }

        .header-right .btn-call .btn-call-text .call-number .call-number {
            color: var(--manchester-red);
            font-weight: 700;
        }

        .header-right .btn-call .btn-call-text .call-number .call-number {
            color: var(--manchester-red);
            font-weight: 700;
        }

        .header-right .btn-call .btn-call-text .call-number .call-number {
            color: var(--manchester-red);
            font-weight: 700;
        }

        .header-right .btn-call .btn-call-text .call-number .call-number {
            color: var(--manchester-red);
            font-weight: 700;
        }

        .header-right .btn-call .btn-call-text .call-number .call-number {
            color: var(--manchester-red);
            font-weight: 700;
        }

        .header-right .btn-call .btn-call-text .call-number .call-number {
            color: var(--manchester-red);
            font-weight: 700;
        }

        .header-right .btn-call .btn-call-text .call-number .call-number {
            color: var(--manchester-red);
            font-weight: 700;
        }

        .header-right .btn-call .btn-call-text .call-number .call-number {
            color: var(--manchester-red);
            font-weight: 700;
        }

        .header-right .btn-call .btn-call-text .call-number .call-number {
            color: var(--manchester-red);
            font-weight: 700;
        }

        .header-right .btn-call .btn-call-text .call-number .call-number {
            color: var(--manchester-red);
            font-weight: 700;
        }

        .header-right .btn-call .btn-call-text .call-number .call-number {
            color: var(--manchester-red);
            font-weight: 700;
        }

        .header-right .btn-call .btn-call-text .call-number .call-number {
            color: var(--manchester-red);
            font-weight: 700;
        }

        .header-right .btn-call .btn-call-text .call-number .call-number {
            color: var(--manchester-red);
            font-weight: 700;
        }

        .header-right .btn-call .btn-call-text .call-number .call-number {
            color: var(--manchester-red);
            font-weight: 700;
        }

        .header-right .btn-call .btn-call-text .call-number .call-number {
            color: var(--manchester-red);
            font-weight: 700;
        }

        .header-right .btn-call .btn-call-text .call-number .call-number {
            color: var(--manchester-red);
            font-weight: 700;
        }

        .header-right .btn-call .btn-call-text .call-number .call-number {
            color: var(--manchester-red);
            font-weight: 700;
        }

        .header-right .btn-call .btn-call-text .call-number .call-number {
            color: var(--manchester-red);
            font-weight: 700;
        }

        .header-right .btn-call .btn-call-text .call-number .call-number {
            color: var(--manchester-red);
            font-weight: 700;
        }

        .header-right .btn-call .btn-call-text .call-number .call-number {
            color: var(--manchester-red);
            font-weight: 700;
        }

        .header-right .btn-call .btn-call-text .call-number .call-number {
            color: var(--manchester-red);
            font-weight: 700;
        }

        .header-right .btn-call .btn-call-text .call-number .call-number {
            color: var(--manchester-red);
            font-weight: 700