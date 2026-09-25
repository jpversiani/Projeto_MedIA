```python
# Arquivo: backend/app/static/painel_triage.html
"""
Painel Visual da Triagem e Monitor de Fila APS (C11)
Projeto MedIA - Atenção Primária / Saúde da Família
TISS ANS 4.01 / DMED Receita Federal
"""

<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Painel Triagem APS - MedIA</title>
    <style>
        /* ============================================
           CSS RESET & VARIABLES
           ============================================ */
        *, *::before, *::after {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        :root {
            --color-manchester-red: #EA3623;
            --color-manchester-dark: #1D1D1D;
            --color-manchester-light: #FFFFFF;
            --color-manchester-gold: #FFC107;
            --color-bg: #F5F5F5;
            --color-card-bg: #FFFFFF;
            --color-text-primary: #1A1A2E;
            --color-text-secondary: #666666;
            --color-text-muted: #999999;
            --color-success: #2ECC71;
            --color-warning: #F39C12;
            --color-danger: #E74C3C;
            --color-info: #3498DB;
            --color-border: #E0E0E0;
            --color-shadow: rgba(0, 0, 0, 0.1);
            --radius-sm: 8px;
            --radius-md: 12px;
            --radius-lg: 16px;
            --radius-xl: 20px;
            --shadow-sm: 0 2px 8px var(--color-shadow);
            --shadow-md: 0 4px 16px var(--color-shadow);
            --shadow-lg: 0 8px 32px var(--color-shadow);
            --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        body {
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: var(--color-bg);
            color: var(--color-text-primary);
            line-height: 1.6;
            min-height: 100vh;
        }

        /* ============================================
           HEADER / NAVBAR
           ============================================ */
        .app-header {
            background: linear-gradient(135deg, var(--color-manchester-red) 0%, #C02828 100%);
            color: var(--color-manchester-light);
            padding: 0;
            position: sticky;
            top: 0;
            z-index: 1000;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
        }

        .header-inner {
            max-width: 1400px;
            margin: 0 auto;
            padding: 12px 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            height: 64px;
        }

        .logo {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .logo-icon {
            width: 40px;
            height: 40px;
            background: var(--color-manchester-gold);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            font-weight: 700;
            color: var(--color-manchester-dark);
        }

        .logo-text {
            font-size: 1.25rem;
            font-weight: 700;
            letter-spacing: 0.5px;
        }

        .logo-text span {
            display: block;
            font-size: 0.7rem;
            opacity: 0.8;
            font-weight: 400;
            letter-spacing: 1px;
            text-transform: uppercase;
        }

        .header-actions {
            display: flex;
            align-items: center;
            gap: 16px;
        }

        .header-btn {
            background: rgba(255, 255, 255, 0.15);
            border: 1px solid rgba(255, 255, 255, 0.3);
            color: white;
            padding: 8px 16px;
            border-radius: var(--radius-sm);
            cursor: pointer;
            font-size: 0.9rem;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: var(--transition);
        }

        .header-btn:hover {
            background: rgba(255, 255, 255, 0.3);
            transform: translateY(-1px);
        }

        .header-btn.active {
            background: var(--color-manchester-gold);
            color: var(--color-manchester-dark);
        }

        .status-indicator {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 14px;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 500;
        }

        .status-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: var(--color-success);
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
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
           STATS BAR
           ============================================ */
        .stats-bar {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }

        .stat-card {
            background: var(--color-card-bg);
            border-radius: var(--radius-md);
            padding: 16px 20px;
            box-shadow: var(--shadow-sm);
            display: flex;
            align-items: center;
            gap: 16px;
            transition: var(--transition);
        }

        .stat-card:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-md);
        }

        .stat-icon {
            width: 48px;
            height: 48px;
            border-radius: var(--radius-sm);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            flex-shrink: 0;
        }

        .stat-icon.red { background: rgba(234, 54, 35, 0.1); color: var(--color-danger); }
        .stat-icon.green { background: rgba(46, 204, 113, 0.1); color: var(--color-success); }
        .stat-icon.blue { background: rgba(52, 152, 219, 0.1); color: var(--color-info); }
        .stat-icon.yellow { background: rgba(243, 156, 18, 0.1); color: var(--color-warning); }

        .stat-content {
            display: flex;
            flex-direction: column;
        }

        .stat-value {
            font-size: 1.75rem;
            font-weight: 700;
            color: var(--color-text-primary);
        }

        .stat-label {
            font-size: 0.85rem;
            color: var(--color-text-secondary);
            margin-top: 2px;
        }

        /* ============================================
           DASHBOARD GRID
           ============================================ */
        .dashboard-grid {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 24px;
            margin-bottom: 24px;
        }

        .dashboard-card {
            background: var(--color-card-bg);
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow-sm);
            overflow: hidden;
        }

        .card-header {
            padding: 20px 24px;
            border-bottom: 1px solid var(--color-border);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .card-title {
            font-size: 1.1rem;
            font-weight: 600;
            color: var(--color-text-primary);
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .card-title .icon {
            font-size: 1.2rem;
        }

        .card-actions {
            display: flex;
            gap: 8px;
        }

        .card-actions button {
            padding: 6px 12px;
            border: 1px solid var(--color-border);
            background: var(--color-bg);
            border-radius: var(--radius-sm);
            cursor: pointer;
            font-size: 0.8rem;
            color: var(--color-text-secondary);
            transition: var(--transition);
        }

        .card-actions button:hover {
            background: var(--color-manchester-red);
            color: white;
            border-color: var(--color-manchester-red);
        }

        .card-body {
            padding: 20px;
        }

        /* ============================================
           TRIAGE CARDS (MANCHESTER STYLE)
           ============================================ */
        .triage-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
            gap: 16px;
        }

        .triage-card {
            border-radius: var(--radius-md);
            padding: 16px;
            cursor: pointer;
            transition: var(--transition);
            position: relative;
            overflow: hidden;
        }

        .triage-card:hover {
            transform: translateY(-3px);
            box-shadow: var(--shadow-md);
        }

        .triage-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
        }

        /* Color-coded priority levels */
        .triage-card.priority-high {
            background: linear-gradient(135deg, #FFF0F0, #FFD4D4);
            border: 2px solid var(--color-danger);
        }
        .triage-card.priority-high::before {
            background: var(--color-danger);
        }

        .triage-card.priority-medium {
            background: linear-gradient(135deg, #FFF8E1, #FFE0B2);
            border: 2px solid var(--color-warning);
        }
        .triage-card.priority-medium::before {
            background: var(--color-warning);
        }

        .triage-card.priority-low {
            background: linear-gradient(135deg, #E8F5E9, #C8E6C9);
            border: 2px solid var(--color-success);
        }
        .triage-card.priority-low::before {
            background: var(--color-success);
        }

        .triage-card.priority-critical {
            background: linear-gradient(135deg, #F3E5F5, #E8D5F5);
            border: 2px solid #9C27B0;
        }
        .triage-card.priority-critical::before {
            background: #9C27B0;
        }

        .triage-card.priority-urgent {
            background: linear-gradient(135deg, #F0F4F8, #D5E0EA);
            border: 2px solid var(--color-info);
        }
        .triage-card.priority-urgent::before {
            background: var(--color-info);
        }

        .triage-card.priority-stable {
            background: linear-gradient(135deg, #F8F9FA, #E9ECEF);
            border: 2px solid var(--color-border);
        }
        .triage-card.priority-stable::before {
            background: var(--color-border);
        }

        .triage-card.priority-observation {
            background: linear-gradient(135deg, #F0F4F8, #D5E0EA);
            border: 2px solid #6C757D;
        }
        .triage-card.priority-observation::before {
            background: #6C757D;
        }

        .triage-card.priority-recovery {
            background: linear-gradient(135deg, #E8F5E9, #C8E6C9);
            border: 2px solid #4CAF50;
        }
        .triage-card.priority-recovery::before {
            background: #4CAF50;
        }

        .triage-card.priority-discharge {
            background: linear-gradient(135deg, #FFF8E1, #FFE0B2);
            border: 2px solid #FF9800;
        }
        .triage-card.priority-discharge::before {
            background: #FF9800;
        }

        .triage-card.priority-consultation {
            background: linear-gradient(135deg, #E3F2FD, #B3E5FC);
            border: 2px solid #0288D1;
        }
