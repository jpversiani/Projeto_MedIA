```python:backend/app/static/painel_triagem.html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Painel de Triagem e Monitor de Fila - APS C59</title>
    <style>
        /* ============================================
           PALETA MANCHESTER (SUS/APS)
           Azul: #004D80 | Verde: #008C3F |
           Verde Escuro: #006B2F | Branco: #FFFFFF
           ============================================ */
        :root {
            --manchester-blue: #004D80;
            --manchester-blue-dark: #00355C;
            --manchester-green: #008C3F;
            --manchester-green-dark: #006B2F;
            --manchester-white: #FFFFFF;
            --manchester-gray: #F5F5F5;
            --manchester-gray-dark: #D3D3D3;
            --manchester-red: #D93025;
            --manchester-orange: #E67E22;
            --shadow-sm: 0 1px 3px rgba(0,0,0,0.08);
            --shadow-md: 0 4px 12px rgba(0,0,0,0.12);
            --shadow-lg: 0 8px 24px rgba(0,0,0,0.15);
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
            background: var(--manchester-gray);
            color: #1a1a2e;
            min-height: 100vh;
            line-height: 1.6;
        }

        /* ============================================
           CABEÇADO
           ============================================ */
        .header {
            background: linear-gradient(135deg, var(--manchester-blue) 0%, var(--manchester-blue-dark) 100%);
            color: var(--manchester-white);
            padding: 16px 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: var(--shadow-md);
            position: sticky;
            top: 0;
            z-index: 1000;
        }

        .header-left {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .header-logo {
            font-size: 1.4rem;
            font-weight: 700;
            letter-spacing: 0.5px;
        }

        .header-logo span {
            color: var(--manchester-green);
        }

        .header-right {
            display: flex;
            align-items: center;
            gap: 16px;
        }

        .status-indicator {
            display: flex;
            align-items: center;
            gap: 8px;
            background: rgba(255,255,255,0.15);
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 0.85rem;
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
            background: var(--manchester-orange);
        }

        .status-dot.critical {
            background: var(--manchester-red);
            animation: pulse 1s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.4; }
        }

        .current-patient-badge {
            background: rgba(255,255,255,0.2);
            padding: 6px 16px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
            backdrop-filter: blur(10px);
        }

        /* ============================================
           LAYOUT PRINCIPAL
           ============================================ */
        .main-container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 24px;
        }

        .dashboard-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 24px;
            margin-bottom: 24px;
        }

        /* ============================================
           CARDS MANCHESTER
           ============================================ */
        .card {
            background: var(--manchester-white);
            border-radius: var(--radius-md);
            box-shadow: var(--shadow-sm);
            padding: 20px;
            transition: var(--transition);
            border: 1px solid var(--manchester-gray);
        }

        .card:hover {
            box-shadow: var(--shadow-md);
            transform: translateY(-2px);
        }

        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 1px solid var(--manchester-gray);
        }

        .card-title {
            font-size: 1rem;
            font-weight: 700;
            color: var(--manchester-blue-dark);
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .card-title .icon {
            font-size: 1.2rem;
        }

        .card-subtitle {
            font-size: 0.8rem;
            color: var(--manchester-gray-dark);
            margin-top: 4px;
        }

        /* Cards por cor Manchester */
        .card-blue {
            border-left: 4px solid var(--manchester-blue);
        }

        .card-green {
            border-left: 4px solid var(--manchester-green);
        }

        .card-red {
            border-left: 4px solid var(--manchester-red);
        }

        .card-orange {
            border-left: 4px solid var(--manchester-orange);
        }

        .card-yellow {
            border-left: 4px solid #F5A623;
        }

        /* ============================================
           METRIKAS PRINCIPAIS
           ============================================ */
        .metric-row {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            margin-bottom: 24px;
        }

        .metric-card {
            background: linear-gradient(135deg, rgba(0,77,128,0.05) 0%, rgba(0,140,63,0.03) 100%);
            border-radius: var(--radius-md);
            padding: 20px;
            text-align: center;
            border: 1px solid rgba(0,77,128,0.1);
        }

        .metric-card .metric-value {
            font-size: 2.5rem;
            font-weight: 800;
            color: var(--manchester-blue);
            line-height: 1;
        }

        .metric-card .metric-label {
            font-size: 0.85rem;
            color: var(--manchester-gray-dark);
            margin-top: 6px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .metric-card .metric-change {
            font-size: 0.75rem;
            font-weight: 600;
            margin-top: 4px;
        }

        .metric-change.positive {
            color: var(--manchester-green);
        }

        .metric-change.negative {
            color: var(--manchester-red);
        }

        /* ============================================
           LISTA DE PACIENTES
           ============================================ */
        .patient-list {
            max-height: 300px;
            overflow-y: auto;
            scrollbar-width: thin;
            scrollbar-color: var(--manchester-gray) var(--manchester-gray-dark);
        }

        .patient-list::-webkit-scrollbar {
            width: 6px;
        }

        .patient-list::-webkit-scrollbar-thumb {
            background: var(--manchester-gray);
            border-radius: 3px;
        }

        .patient-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px 16px;
            border-radius: var(--radius-sm);
            margin-bottom: 8px;
            transition: var(--transition);
            cursor: default;
        }

        .patient-item:hover {
            background: rgba(0,77,128,0.03);
        }

        .patient-item.active {
            background: linear-gradient(135deg, rgba(0,77,128,0.08) 0%, rgba(0,140,63,0.05) 100%);
            border: 2px solid var(--manchester-blue);
        }

        .patient-item .patient-number {
            font-weight: 800;
            color: var(--manchester-blue);
            font-size: 1.1rem;
            min-width: 30px;
        }

        .patient-item .patient-info {
            flex: 1;
        }

        .patient-item .patient-name {
            font-weight: 600;
            color: #1a1a2e;
            font-size: 0.95rem;
        }

        .patient-item .patient-cns {
            font-size: 0.75rem;
            color: var(--manchester-gray-dark);
            margin-top: 2px;
        }

        .patient-item .patient-status {
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        }

        .patient-item .patient-status.waiting {
            background: rgba(0,77,128,0.1);
            color: var(--manchester-blue);
        }

        .patient-item .patient-status.calling {
            background: rgba(210,48,37,0.1);
            color: var(--manchester-red);
            animation: pulse 1s infinite;
        }

        .patient-item .patient-status.attending {
            background: rgba(0,140,63,0.1);
            color: var(--manchester-green);
        }

        .patient-item .patient-status.completed {
            background: rgba(0,140,63,0.1);
            color: var(--manchester-green);
        }

        .patient-item .patient-wait {
            font-size: 0.85rem;
            color: var(--manchester-gray-dark);
            font-weight: 500;
        }

        .patient-item .patient-wait.critical {
            color: var(--manchester-red);
            font-weight: 700;
        }

        /* ============================================
           PANEL DE ERMENGA
           ============================================ */
        .nursing-panel {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
        }

        .nurse-card {
            background: linear-gradient(135deg, rgba(0,140,63,0.03) 0%, rgba(0,77,128,0.03) 100%);
            border-radius: var(--radius-md);
            padding: 16px;
            border: 1px solid rgba(0,140,63,0.1);
        }

        .nurse-card .nurse-name {
            font-weight: 700;
            color: var(--manchester-blue-dark);
            font-size: 0.95rem;
        }

        .nurse-card .nurse-role {
            font-size: 0.75rem;
            color: var(--manchester-gray-dark);
            margin-top: 2px;
        }

        .nurse-card .nurse-patients {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-top: 10px;
        }

        .patient-count {
            background: var(--manchester-blue);
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 700;
        }

        .patient-count.high {
            background: var(--manchester-red);
        }

        .patient-count.medium {
            background: var(--manchester-orange);
        }

        .patient-count.low {
            background: var(--manchester-green);
        }

        .nurse-card .nurse-patient-list {
            margin-top: 8px;
            padding-top: 8px;
            border-top: 1px solid var(--manchester-gray);
        }

        .nurse-card .nurse-patient-list .patient-item {
            padding: 4px 8px;
            font-size: 0.8rem;
            border-radius: 4px;
        }

        /* ============================================
           BLOCO DE CHAMADA SONORA
           ============================================ */
        .sound-call-block {
            background: linear-gradient(135deg, rgba(210,48,37,0.05) 0%, rgba(230,126,34,0.03) 100%);
            border-radius: var(--radius-md);
            padding: 