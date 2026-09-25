```html:backend/app/static/painel_triagem.html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Painel de Triagem e Monitor de Fila - C3 (SUS/APS)</title>
    <style>
        /* ============================================
           CSS RESET & VARIABLES (Manchester Colors)
           ============================================ */
        :root {
            --man-blue: #003388;
            --man-blue-light: #0055aa;
            --man-blue-dark: #002266;
            --man-white: #ffffff;
            --man-green: #008800;
            --man-green-light: #00aa00;
            --man-red: #cc0000;
            --man-red-light: #ff4444;
            --man-yellow: #ffff00;
            --man-orange: #ff8800;
            --man-gray: #888888;
            --man-gray-light: #e8e8e8;
            --man-gray-dark: #333333;
            --shadow-sm: 0 2px 4px rgba(0,0,0,0.1);
            --shadow-md: 0 4px 12px rgba(0,0,0,0.15);
            --shadow-lg: 0 8px 24px rgba(0,0,0,0.2);
            --radius-sm: 8px;
            --radius-md: 12px;
            --radius-lg: 16px;
            --transition: all 0.3s ease;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: var(--man-gray-light);
            color: var(--man-gray-dark);
            min-height: 100vh;
        }

        /* ============================================
           HEADER / BARRA DE NAVEGAÇÃO
           ============================================ */
        .app-header {
            background: var(--man-blue);
            color: var(--man-white);
            padding: 12px 24px;
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

        .header-brand .logo {
            width: 40px;
            height: 40px;
            background: var(--man-white);
            border-radius: var(--radius-sm);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 900;
            font-size: 18px;
            color: var(--man-blue-dark);
        }

        .header-brand h1 {
            font-size: 1.2rem;
            font-weight: 700;
            letter-spacing: 0.5px;
        }

        .header-brand h1 span {
            color: var(--man-green);
        }

        .header-right {
            display: flex;
            align-items: center;
            gap: 16px;
        }

        .header-right .stat-badge {
            background: var(--man-white);
            color: var(--man-blue-dark);
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .header-right .stat-badge .pulse {
            width: 8px;
            height: 8px;
            background: var(--man-green);
            border-radius: 50%;
            animation: pulse 2s infinite;
        }

        .header-right .stat-badge .pulse.red {
            background: var(--man-red);
        }

        .header-right .stat-badge .pulse.yellow {
            background: var(--man-yellow);
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.4; }
        }

        .header-right .nav-links {
            display: flex;
            gap: 8px;
        }

        .header-right .nav-links a {
            color: var(--man-white);
            text-decoration: none;
            padding: 8px 16px;
            border-radius: var(--radius-sm);
            font-size: 0.9rem;
            transition: var(--transition);
        }

        .header-right .nav-links a:hover {
            background: rgba(255,255,255,0.2);
        }

        .header-right .nav-links a.active {
            background: var(--man-white);
            color: var(--man-blue-dark);
        }

        /* ============================================
           MAIN LAYOUT
           ============================================ */
        .main-container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }

        .page-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 20px;
            padding: 16px 20px;
            background: var(--man-white);
            border-radius: var(--radius-md);
            box-shadow: var(--shadow-sm);
        }

        .page-header h2 {
            font-size: 1.3rem;
            color: var(--man-blue-dark);
        }

        .page-header h2 .subtitle {
            font-size: 0.85rem;
            color: var(--man-gray);
            margin-top: 2px;
        }

        .page-header .filters {
            display: flex;
            gap: 8px;
            align-items: center;
        }

        .filter-btn {
            padding: 6px 14px;
            border: 1px solid var(--man-gray-light);
            background: var(--man-white);
            border-radius: 20px;
            cursor: pointer;
            font-size: 0.85rem;
            color: var(--man-gray-dark);
            transition: var(--transition);
        }

        .filter-btn:hover {
            border-color: var(--man-blue);
            color: var(--man-blue);
        }

        .filter-btn.active {
            background: var(--man-blue);
            color: var(--man-white);
            border-color: var(--man-blue);
        }

        /* ============================================
           CARDS GRID
           ============================================ */
        .cards-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }

        .card {
            background: var(--man-white);
            border-radius: var(--radius-md);
            box-shadow: var(--shadow-sm);
            padding: 20px;
            transition: var(--transition);
            border-left: 4px solid transparent;
        }

        .card:hover {
            box-shadow: var(--shadow-md);
            transform: translateY(-2px);
        }

        .card.man-blue {
            border-left-color: var(--man-blue);
        }

        .card.man-green {
            border-left-color: var(--man-green);
        }

        .card.man-red {
            border-left-color: var(--man-red);
        }

        .card.man-yellow {
            border-left-color: var(--man-yellow);
        }

        .card.man-orange {
            border-left-color: var(--man-orange);
        }

        .card-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 16px;
        }

        .card-title {
            font-size: 1rem;
            font-weight: 700;
            color: var(--man-gray-dark);
        }

        .card-status {
            font-size: 0.75rem;
            padding: 3px 10px;
            border-radius: 12px;
            font-weight: 600;
        }

        .card-status.critical {
            background: rgba(255,0,0,0.1);
            color: var(--man-red);
        }

        .card-status.warning {
            background: rgba(255,255,0,0.1);
            color: var(--man-orange);
        }

        .card-status.normal {
            background: rgba(0,136,0,0.1);
            color: var(--man-green);
        }

        .card-status.resolved {
            background: rgba(0,51,136,0.1);
            color: var(--man-blue);
        }

        /* ============================================
           METRICS DISPLAY
           ============================================ */
        .metric-value {
            font-size: 2.5rem;
            font-weight: 900;
            color: var(--man-blue-dark);
            line-height: 1;
        }

        .metric-label {
            font-size: 0.85rem;
            color: var(--man-gray);
            margin-top: 4px;
        }

        .metric-sub {
            font-size: 0.8rem;
            color: var(--man-gray-light);
            margin-top: 2px;
        }

        .metric-change {
            font-size: 0.85rem;
            font-weight: 600;
            padding: 2px 8px;
            border-radius: 10px;
        }

        .metric-change.up {
            background: rgba(0,136,0,0.1);
            color: var(--man-green);
        }

        .metric-change.down {
            background: rgba(255,0,0,0.1);
            color: var(--man-red);
        }

        /* ============================================
           TRIAGE LEVELS (C3)
           ============================================ */
        .triage-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 12px;
        }

        .triage-level {
            padding: 12px 10px;
            border-radius: var(--radius-sm);
            text-align: center;
            cursor: pointer;
            transition: var(--transition);
            border: 2px solid transparent;
        }

        .triage-level:hover {
            transform: scale(1.05);
        }

        .triage-level.c3-urgent {
            background: rgba(255,0,0,0.1);
            border-color: var(--man-red);
            color: var(--man-red);
        }

        .triage-level.c3-urgent:hover {
            background: rgba(255,0,0,0.2);
        }

        .triage-level.c3-urgent .level-number {
            font-size: 1.5rem;
            font-weight: 900;
        }

        .triage-level.c3-urgent .level-label {
            font-size: 0.7rem;
            font-weight: 600;
        }

        .triage-level.c3-urgent .level-count {
            background: var(--man-red);
            color: white;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 0.75rem;
            font-weight: 700;
        }

        .triage-level.c3-urgent-2 {
            background: rgba(255,255,0,0.1);
            border-color: var(--man-orange);
            color: var(--man-orange);
        }

        .triage-level.c3-urgent-2:hover {
            background: rgba(255,255,0,0.2);
        }

        .triage-level.c3-urgent-2 .level-number {
            font-size: 1.5rem;
            font-weight: 900;
        }

        .triage-level.c3-urgent-2 .level-label {
            font-size: 0.7rem;
            font-weight: 600;
        }

        .triage-level.c3-urgent-2 .level-count {
            background: var(--man-orange);
            color: white;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 0.75rem;
            font-weight: 700;
        }

        .triage-level.c3-urgent-3 {
            background: rgba(255,255,0,0.1);
            border-color: var(--man-yellow);
            color: var(--man-yellow);
        }

        .triage-level.c3-urgent-3:hover {
            background: rgba(255,255,0,0.2);
        }

        .triage-level.c3-urgent-3 .level-number {
            font-size: 1.5rem;
            font-weight: 900;
        }

        .triage-level.c3-urgent-3 .level-label {
            font-size: 0.7rem;
            font-weight: 600;
        }

        .triage-level.c3-urgent-3 .level-count {
            background: var(--man-yellow);
            color: var(--man-gray-dark);
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 0.75rem;
            font-weight: 700;
        }

        .triage-level.c3-normal {
            background: rgba(0,136,0,0.1);
            border-color: var(--man-green);
            color: var(--man-green);
        }

        .triage-level.c3-normal:hover {
            background: rgba(0,136,0,0.2);
        }

        .triage-level.c3-normal .level-number {
            font-size: 1.5rem;
            font-weight: 900;
        }

        .triage-level.c3-normal .level-label {
            font-size: 0.7rem;
            font-weight: 600;
        }

        .triage-level.c3-normal .level-count {
            background: var(--man-green);
            color: white;
            padding: 2px 8px;
