```html:backend/app/static/painel_triage.html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Painel de Triagem e Monitor de Fila - C43</title>
    <style>
        /* ============================================
           MANCHESTER COLORS & THEME
           ============================================ */
        :root {
            --color-red: #e74c3c;
            --color-red-dark: #c0392b;
            --color-green: #2ecc71;
            --color-green-dark: #27ae60;
            --color-blue: #3498db;
            --color-blue-dark: #2980b9;
            --color-yellow: #f1c40f;
            --color-yellow-dark: #d6a94e;
            --color-orange: #e67e22;
            --color-orange-dark: #c0392b;
            --color-purple: #9b59b6;
            --color-purple-dark: #8e44ad;
            --color-cyan: #1abc9c;
            --color-cyan-dark: #16a085;
            --color-gray-50: #f8f9fa;
            --color-gray-100: #e9ecef;
            --color-gray-200: #dee2e6;
            --color-gray-300: #ced4da;
            --color-gray-400: #bac3c7;
            --color-gray-500: #6c757d;
            --color-gray-600: #495057;
            --color-gray-700: #343a40;
            --color-gray-800: #2d3748;
            --color-gray-900: #1a202c;
            --color-white: #ffffff;
            --shadow-sm: 0 1px 3px rgba(0,0,0,0.12);
            --shadow-md: 0 4px 6px rgba(0,0,0,0.1), 0 2px 4px rgba(0,0,0,0.06);
            --shadow-lg: 0 10px 15px rgba(0,0,0,0.1), 0 4px 6px rgba(0,0,0,0.05);
            --shadow-xl: 0 20px 25px rgba(0,0,0,0.1), 0 8px 10px rgba(0,0,0,0.06);
            --radius-sm: 6px;
            --radius-md: 10px;
            --radius-lg: 16px;
            --radius-xl: 24px;
            --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: var(--color-gray-50);
            color: var(--color-gray-800);
            line-height: 1.6;
            min-height: 100vh;
        }

        /* ============================================
           HEADER / NAVBAR
           ============================================ */
        .app-header {
            background: linear-gradient(135deg, var(--color-blue) 0%, var(--color-blue-dark) 100%);
            color: var(--color-white);
            padding: 0;
            box-shadow: var(--shadow-lg);
            position: sticky;
            top: 0;
            z-index: 1000;
        }

        .header-inner {
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 24px;
            height: 72px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .logo {
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 1.25rem;
            font-weight: 700;
            letter-spacing: -0.5px;
        }

        .logo-icon {
            width: 40px;
            height: 40px;
            background: var(--color-white);
            border-radius: var(--radius-sm);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.25rem;
        }

        .header-right {
            display: flex;
            align-items: center;
            gap: 16px;
        }

        .header-status {
            display: flex;
            align-items: center;
            gap: 8px;
            background: rgba(255,255,255,0.15);
            padding: 8px 16px;
            border-radius: 50px;
            font-size: 0.875rem;
            font-weight: 600;
            backdrop-filter: blur(10px);
        }

        .status-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: var(--color-green);
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .header-right .btn {
            background: var(--color-white);
            color: var(--color-gray-800);
            border: none;
            padding: 8px 16px;
            border-radius: var(--radius-sm);
            cursor: pointer;
            font-size: 0.875rem;
            font-weight: 600;
            transition: var(--transition);
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .header-right .btn:hover {
            transform: translateY(-1px);
            box-shadow: var(--shadow-md);
        }

        .header-right .btn-danger {
            background: var(--color-red);
            color: var(--color-white);
        }

        .header-right .btn-danger:hover {
            background: var(--color-red-dark);
        }

        /* ============================================
           MAIN CONTENT
           ============================================ */
        .main-content {
            max-width: 1400px;
            margin: 0 auto;
            padding: 24px;
        }

        /* ============================================
           PAGE TITLE
           ============================================ */
        .page-title {
            margin-bottom: 24px;
        }

        .page-title h1 {
            font-size: 1.75rem;
            font-weight: 800;
            color: var(--color-gray-900);
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .page-title h1 .icon {
            font-size: 1.5rem;
        }

        .page-title .subtitle {
            font-size: 0.9375rem;
            color: var(--color-gray-600);
            margin-top: 4px;
        }

        /* ============================================
           KPI CARDS (MANCHESTER COLORS)
           ============================================ */
        .kpi-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 24px;
        }

        .kpi-card {
            background: var(--color-white);
            border-radius: var(--radius-lg);
            padding: 20px;
            box-shadow: var(--shadow-sm);
            transition: var(--transition);
            border: 1px solid var(--color-gray-200);
        }

        .kpi-card:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-md);
        }

        .kpi-card.red { border-left: 4px solid var(--color-red); }
        .kpi-card.green { border-left: 4px solid var(--color-green); }
        .kpi-card.blue { border-left: 4px solid var(--color-blue); }
        .kpi-card.yellow { border-left: 4px solid var(--color-yellow); }
        .kpi-card.orange { border-left: 4px solid var(--color-orange); }
        .kpi-card.purple { border-left: 4px solid var(--color-purple); }

        .kpi-card .kpi-icon {
            font-size: 1.5rem;
            margin-bottom: 12px;
        }

        .kpi-card .kpi-label {
            font-size: 0.8125rem;
            color: var(--color-gray-500);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-weight: 600;
            margin-bottom: 4px;
        }

        .kpi-card .kpi-value {
            font-size: 1.75rem;
            font-weight: 800;
            color: var(--color-gray-900);
        }

        .kpi-card .kpi-change {
            font-size: 0.75rem;
            font-weight: 600;
            margin-top: 6px;
        }

        .kpi-card .kpi-change.positive { color: var(--color-green); }
        .kpi-card .kpi-change.negative { color: var(--color-red); }

        /* ============================================
           DASHBOARD GRID
           ============================================ */
        .dashboard-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 24px;
            margin-bottom: 24px;
        }

        .dashboard-card {
            background: var(--color-white);
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow-sm);
            border: 1px solid var(--color-gray-200);
            overflow: hidden;
        }

        .dashboard-card-header {
            padding: 20px 24px;
            border-bottom: 1px solid var(--color-gray-200);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .dashboard-card-header h2 {
            font-size: 1rem;
            font-weight: 700;
            color: var(--color-gray-800);
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .dashboard-card-header .badge {
            padding: 4px 10px;
            border-radius: 50px;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .badge-red { background: rgba(231,76,60,0.1); color: var(--color-red); }
        .badge-green { background: rgba(46,204,113,0.1); color: var(--color-green); }
        .badge-blue { background: rgba(52,152,219,0.1); color: var(--color-blue); }
        .badge-yellow { background: rgba(241,196,15,0.1); color: var(--color-orange); }

        .dashboard-card-body {
            padding: 24px;
        }

        /* ============================================
           TRIAGE QUEUE TABLE
           ============================================ */
        .queue-table {
            width: 100%;
            border-collapse: collapse;
        }

        .queue-table th {
            text-align: left;
            padding: 12px 16px;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--color-gray-500);
            background: var(--color-gray-50);
            border-bottom: 2px solid var(--color-gray-200);
        }

        .queue-table td {
            padding: 14px 16px;
            font-size: 0.875rem;
            border-bottom: 1px solid var(--color-gray-100);
            color: var(--color-gray-700);
        }

        .queue-table tr:hover {
            background: var(--color-gray-50);
        }

        .queue-table tr:last-child td {
            border-bottom: none;
        }

        .patient-number {
            font-weight: 700;
            color: var(--color-blue);
        }

        .patient-name {
            font-weight: 600;
            color: var(--color-gray-800);
        }

        .patient-name .initials {
            display: block;
            font-size: 0.75rem;
            color: var(--color-gray-500);
            margin-top: 2px;
        }

        .patient-cns {
            font-family: monospace;
            font-size: 0.8rem;
            color: var(--color-gray-500);
            background: var(--color-gray-100);
            padding: 2px 8px;
            border-radius: 4px;
        }

        .patient-age {
            color: var(--color-gray-600);
        }

        .patient-gender {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            padding: 3px 8px;
            border-radius: 50px;
            font-size: 0.75rem;
            font-weight: 600;
        }

        .patient-gender.m {
            background: rgba(52,152,219,0.1);
            color: var(--color-blue);
        }

        .patient-gender.f {
            background: rgba(231,76,60,0.1);
            color: var(--color-red);
        }

        .patient-gender.o {
            background: rgba(241,196,15,0.1);
            color: var(--color-orange);
        }

        .patient-status {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 10px;
            border-radius: 50px;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0